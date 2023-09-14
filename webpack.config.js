const createExpoWebpackConfigAsync = require('@expo/webpack-config');

module.exports = async function (env, argv) {
  const config = await createExpoWebpackConfigAsync(env, argv);
  // Customize the config before returning it.

  config.devServer = {
    proxy: {
      // with options: http://localhost:5173/api/bar-> http://jsonplaceholder.typicode.com/bar
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/chain': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/fetch': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/streaming/ask': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  }

  return config;
};
