module.exports = {
    content: ["./templates/**/*.{html,js}", 
    "./static/scripts/*.{html,js}",],
    safelist:{
      options:["bg-blue-900", "hover:bg-blue-900"]
    },
    theme: {
      extend: {},
      // fontFamily: {
      //   "share-tech": ["Share Tech Mono", "monospace"],
      // }
    },
    plugins: [],
  }