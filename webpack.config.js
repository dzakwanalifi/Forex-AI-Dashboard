const path = require('path');

module.exports = {
  entry: {
    dashboard: './static/js/dashboard.js',
    lstm_model: './static/js/lstm_model.js'
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, 'static/dist'),
  },
  mode: 'development',
  watch: true,
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      }
    ]
  }
};
