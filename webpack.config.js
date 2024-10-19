const path = require('path');

module.exports = {
  entry: './static/js/dashboard.js',
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'static/dist'),
  },
  mode: 'development',
  watch: true,
};
