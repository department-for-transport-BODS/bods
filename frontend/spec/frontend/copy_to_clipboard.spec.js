const copyToClipboard = require("../../frontend/assets/js/copy_to_clipboard");

describe("CopyToClipboard", () => {
  it("should call document execute copy", () => {
    const spyExec = spyOn(document, "execCommand");

    // Test
    copyToClipboard("Some text");

    // Assert
    expect(spyExec).toHaveBeenCalledWith("copy");
  });
});
