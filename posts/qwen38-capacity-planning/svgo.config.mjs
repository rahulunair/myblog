export default {
  plugins: [
    {
      name: "preset-default",
      params: {
        overrides: {
          removeTitle: false,
          removeDesc: false,
          removeUnknownsAndDefaults: {
            keepRoleAttr: true,
          },
        },
      },
    },
    "removeDimensions",
  ],
};
