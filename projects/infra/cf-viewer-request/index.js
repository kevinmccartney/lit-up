'use strict';

// NOTE: Lambda@Edge does not support environment variables.
// We fetch config (active versions + basic auth creds) from SSM Parameter Store.
// Node.js 18 Lambda@Edge does not include aws-sdk, so call SSM directly over HTTPS (SigV4).
const https = require('https');
const crypto = require('crypto');

const SSM_AUTH_USERNAME_PARAM = '${ssm_auth_username_param}';
const SSM_AUTH_PASSWORD_PARAM = '${ssm_auth_password_param}';
const SSM_ACTIVE_VERSIONS_PARAM = '${ssm_active_versions_param}';

const CONFIG_CACHE_MS = 60 * 1000; // cache SSM lookups for 60s per edge container
let cachedConfig = null;
let cachedConfigAtMs = 0;

function sha256Hex(data) {
  return crypto.createHash('sha256').update(data, 'utf8').digest('hex');
}

function hmac(key, data, encoding) {
  return crypto.createHmac('sha256', key).update(data, 'utf8').digest(encoding);
}

function getAmzDate(now) {
  // YYYYMMDD'T'HHMMSS'Z'
  return now.toISOString().replace(/[:-]|\.\d{3}/g, '');
}

function signAwsRequest({
  method,
  host,
  path,
  region,
  service,
  headers,
  body,
  accessKeyId,
  secretAccessKey,
  sessionToken,
}) {
  const amzDate = getAmzDate(new Date());
  const dateStamp = amzDate.slice(0, 8);

  const canonicalUri = path || '/';
  const canonicalQueryString = '';

  const lowerHeaders = {};
  Object.keys(headers || {}).forEach((k) => {
    lowerHeaders[k.toLowerCase()] = String(headers[k]).trim();
  });

  lowerHeaders.host = host;
  lowerHeaders['x-amz-date'] = amzDate;
  if (sessionToken) lowerHeaders['x-amz-security-token'] = sessionToken;

  const signedHeaderKeys = Object.keys(lowerHeaders).sort();
  const canonicalHeaders = signedHeaderKeys
    .map((k) => k + ':' + lowerHeaders[k] + '\n')
    .join('');
  const signedHeaders = signedHeaderKeys.join(';');

  const payloadHash = sha256Hex(body || '');
  const canonicalRequest = [
    method,
    canonicalUri,
    canonicalQueryString,
    canonicalHeaders,
    signedHeaders,
    payloadHash,
  ].join('\n');

  const algorithm = 'AWS4-HMAC-SHA256';
  const credentialScope = dateStamp + '/' + region + '/' + service + '/aws4_request';
  const stringToSign = [
    algorithm,
    amzDate,
    credentialScope,
    sha256Hex(canonicalRequest),
  ].join('\n');

  const kDate = hmac('AWS4' + secretAccessKey, dateStamp);
  const kRegion = hmac(kDate, region);
  const kService = hmac(kRegion, service);
  const kSigning = hmac(kService, 'aws4_request');
  const signature = hmac(kSigning, stringToSign, 'hex');

  const authorizationHeader =
    algorithm +
    ' Credential=' +
    accessKeyId +
    '/' +
    credentialScope +
    ', SignedHeaders=' +
    signedHeaders +
    ', Signature=' +
    signature;

  return { amzDate, authorizationHeader, securityToken: sessionToken };
}

function httpsJsonRequest({ host, method, path, headers, body }) {
  return new Promise((resolve, reject) => {
    const req = https.request({ host, method, path, headers }, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(data || '{}'));
          } catch (e) {
            reject(new Error('Failed to parse JSON response: ' + e + '. Body=' + data));
          }
          return;
        }
        reject(
          new Error(
            'HTTP ' +
              res.statusCode +
              ' from ' +
              host +
              path +
              '. Body=' +
              (data || ''),
          ),
        );
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

function parseVersions(csv) {
  return (csv || '')
    .split(',')
    .map((v) => v.trim())
    .filter((v) => v.length > 0);
}

async function loadConfig() {
  const now = Date.now();
  if (cachedConfig && now - cachedConfigAtMs < CONFIG_CACHE_MS) {
    return cachedConfig;
  }

  const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
  const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;
  const sessionToken = process.env.AWS_SESSION_TOKEN;

  if (!accessKeyId || !secretAccessKey) {
    throw new Error('Missing AWS credentials in environment');
  }

  const region = 'us-east-1';
  const host = 'ssm.' + region + '.amazonaws.com';
  const method = 'POST';
  const path = '/';
  const body = JSON.stringify({
    Names: [
      SSM_AUTH_USERNAME_PARAM,
      SSM_AUTH_PASSWORD_PARAM,
      SSM_ACTIVE_VERSIONS_PARAM,
    ],
    WithDecryption: true,
  });

  const baseHeaders = {
    'content-type': 'application/x-amz-json-1.1',
    'x-amz-target': 'AmazonSSM.GetParameters',
  };

  const sig = signAwsRequest({
    method,
    host,
    path,
    region,
    service: 'ssm',
    headers: baseHeaders,
    body,
    accessKeyId,
    secretAccessKey,
    sessionToken,
  });

  const headers = {
    ...baseHeaders,
    host,
    'x-amz-date': sig.amzDate,
    authorization: sig.authorizationHeader,
  };
  if (sig.securityToken) headers['x-amz-security-token'] = sig.securityToken;

  const resp = await httpsJsonRequest({ host, method, path, headers, body });

  const params = new Map((resp.Parameters || []).map((p) => [p.Name, p.Value]));

  const authUser = params.get(SSM_AUTH_USERNAME_PARAM);
  const authPass = params.get(SSM_AUTH_PASSWORD_PARAM);
  const activeVersionsCsv = params.get(SSM_ACTIVE_VERSIONS_PARAM) || 'v1';

  if (!authUser || !authPass) {
    const invalid = (resp.InvalidParameters || []).join(', ');
    const errString =
      'Missing auth parameters in SSM. invalid=' +
      invalid +
      ' userParam=' +
      SSM_AUTH_USERNAME_PARAM +
      ' passParam=' +
      SSM_AUTH_PASSWORD_PARAM;
    throw new Error(errString);
  }

  const activeVersions = parseVersions(activeVersionsCsv);
  const defaultVersion = activeVersions[0] || 'v1';

  cachedConfig = {
    authUser,
    authPass,
    authString: 'Basic ' + Buffer.from(authUser + ':' + authPass).toString('base64'),
    activeVersions,
    defaultVersion,
  };
  cachedConfigAtMs = now;
  return cachedConfig;
}

function applyVersionRouting(request, cfg) {
  const uri = request.uri || '/';

  // If no path is given ("/"), send users to the default version's index
  if (uri === '/' || uri === '') {
    request.uri = '/' + cfg.defaultVersion + '/index.html';
    return request;
  }

  // If the URI contains a period, it is for a static file (HTML, CSS, JS, MP3, images, etc.)
  if (uri.includes('.')) {
    // Check if the URI already starts with a version prefix (e.g., /v1/playlist.mp3)
    const trimmed = uri.replace(/^\/+/, ''); // remove leading slashes
    const [firstSegment] = trimmed.split('/');

    // If it already starts with a version prefix, leave it alone
    if (/^v\d+$/i.test(firstSegment)) {
      return request;
    }

    // Otherwise, prepend the default version prefix (e.g., /playlist.mp3 -> /v1/playlist.mp3)
    request.uri = '/' + cfg.defaultVersion + uri;
    return request;
  }

  // If a versioned path is given (e.g. /v1/foo, /v3/bar), route to that version's index.html
  const trimmed = uri.replace(/^\/+/, ''); // remove leading slashes
  const [firstSegment] = trimmed.split('/');

  if (/^v\d+$/i.test(firstSegment)) {
    const normalizedVersion = firstSegment.toLowerCase();

    // If the requested version exists, use it; otherwise, fall back to default version
    if (cfg.activeVersions.map((v) => v.toLowerCase()).includes(normalizedVersion)) {
      request.uri = '/' + normalizedVersion + '/index.html';
    } else {
      request.uri = '/' + cfg.defaultVersion + '/index.html';
    }

    return request;
  }

  // For all other React routes, fall back to the default version's index.html
  request.uri = '/' + cfg.defaultVersion + '/index.html';

  return request;
}

exports.handler = async (event) => {
  try {
    const request = event.Records[0].cf.request;
    const headers = request.headers;
    const uri = request.uri || '/';

    // Check if this is a public file that doesn't require authentication
    // Public files: /manifest.json, /sw.js (and their versioned variants like /v1/manifest.json)
    const isPublicFile =
      uri === '/manifest.json' ||
      uri === '/sw.js' ||
      uri.endsWith('/manifest.json') ||
      uri.endsWith('/sw.js');

    const cfg = await loadConfig();

    // Check if authorization header exists and matches (or if it's a public file)
    if (
      isPublicFile ||
      (headers.authorization && headers.authorization[0].value === cfg.authString)
    ) {
      // User is authenticated (or accessing public file), apply version-based routing
      const routedRequest = applyVersionRouting(request, cfg);

      console.log('request uri: ' + routedRequest.uri);
      return routedRequest;
    } else {
      // User is not authenticated, return 401 with Basic Auth challenge
      return {
        status: '401',
        statusDescription: 'Unauthorized',
        headers: {
          'www-authenticate': [
            {
              key: 'WWW-Authenticate',
              value: 'Basic realm="Secure Area"',
            },
          ],
          'cache-control': [
            {
              key: 'Cache-Control',
              value: 'no-cache',
            },
          ],
        },
      };
    }
  } catch (error) {
    console.error('error: ' + error);
    return {
      status: '500',
      statusDescription: 'Internal Server Error',
      headers: {
        'content-type': [
          {
            key: 'Content-Type',
            value: 'text/plain',
          },
        ],
      },
      body: 'Server error',
    };
  }
};
