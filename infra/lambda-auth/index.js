"use strict";

exports.handler = (event, context, callback) => {
  const request = event.Records[0].cf.request;
  const headers = request.headers;

  // Credentials are embedded via Terraform templatefile()
  const authUser = "${auth_username}";
  const authPass = "${auth_password}";

  // Create the expected Basic Auth string
  const authString =
    "Basic " + Buffer.from(authUser + ":" + authPass).toString("base64");

  // Check if authorization header exists and matches
  if (headers.authorization && headers.authorization[0].value === authString) {
    // User is authenticated, allow request to proceed
    callback(null, request);
  } else {
    // User is not authenticated, return 401 with Basic Auth challenge
    const response = {
      status: "401",
      statusDescription: "Unauthorized",
      headers: {
        "www-authenticate": [
          {
            key: "WWW-Authenticate",
            value: 'Basic realm="Secure Area"',
          },
        ],
        "cache-control": [
          {
            key: "Cache-Control",
            value: "no-cache",
          },
        ],
      },
    };
    callback(null, response);
  }
};
