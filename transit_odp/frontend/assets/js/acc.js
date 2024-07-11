import axe from "axe-core";

async function fetchSync(resultsViolations) {
  try {
    console.log("fetching violations");
    const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const formData = new FormData();
    formData.append("violation", JSON.stringify(resultsViolations));
    formData.append("csrfmiddlewaretoken", csrf);
    formData.append("url", window.location.href);

    const req = new Request("/api/acc/", {
      method: 'POST',
      body: formData,
    });

    const response = await fetch(req);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    const data = await response.json(); // Process your data here
    console.log(data);
  } catch (error) {
    console.error("Fetch error: ", error);
  }
}

axe.run({ xpath: true, reporter: "v2", ancestry: true, absolutePaths: true, elementRef: true }, (err, results) => {
  if (err) {
    console.log(err)
    console.error('Something bad happened:', err.message);
  } else {
    fetchSync(results);
  }
});
