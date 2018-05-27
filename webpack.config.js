const path = require('path');

module.exports = {
  entry: './static/scripts/main.js',
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'static/scripts')
  }
};
