// This will replace the 409 Conflict-Notice which happens, when a file is
// too large to preview, with a nicer error message.
// It needs to load without a module as it needs to change content in an iFrame.
// The time-out makes sure that everything is loaded before the error message.

const myTimeout = setTimeout(replace409Error, 2000);

function replace409Error() {
  text = $("iframe").contents().find('h1').html()

  if (typeof text === "string") {
    if (text.includes("409 Conflict")) {
      div = $("iframe").contents().find('div:first');
      div.html("" +
          "<pre data-module=\"text_view\">\n" +
          " \n" +
          "  <title>409 Conflict</title>\n" +
          " \n" +
          " \n" +
          "  <h1>Preview can not be loaded</h1>\n" +
          "  The content of this file is too large to preview.<br><br>\n" +
          "<b>Error: 409 Conflict</b> Content is too large to be proxied.\n" +
          "\n" +
          " \n" +
          "</pre>")
    }
  }
}