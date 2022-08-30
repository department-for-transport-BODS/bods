const maxNumOfChars = 1200;

export class CounterCharactersInTextBox {
  constructor(textAreaId, characterCounterId) {
    this.textArea = document.getElementById(textAreaId);
    this.characterCounter = document.getElementById(characterCounterId);
    this.characterCounter.textContent =
      maxNumOfChars - this.textArea.value.length;
    this.init();
  }

  init() {
    this.textArea.addEventListener("input", () => {
      let numOfEnteredChars = this.textArea.value.length;
      let counter = maxNumOfChars - numOfEnteredChars;
      this.characterCounter.textContent = counter;
    });
  }
}
