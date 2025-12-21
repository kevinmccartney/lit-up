/**
 * Minimal stub Lambda for API Gateway (proxy integration).
 * Returns "pong" (and echoes basic request info).
 */
exports.handler = async (event) => {
  return {
    statusCode: 200,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
    },
    body: JSON.stringify({
      pong: true,
      requestId: event?.requestContext?.requestId ?? null,
      path: event?.path ?? null,
      httpMethod: event?.httpMethod ?? null,
    }),
  };
};
