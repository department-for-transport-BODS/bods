import axe from "axe-core";

async function fetchSync(resultsViolations) {
  try {

    const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
    console.log(csrf);
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

axe.run().then(async results => {
  if (results.violations.length) {
    console.log(results.violations);
    fetchSync(results.violations);
  }
}).catch(err => {
  console.log(err)
  console.error('Something bad happened:', err.message);
});
