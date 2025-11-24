document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("addBtn");
  const resultEl = document.getElementById("result");

  btn.addEventListener("click", async () => {
    const a = Number(document.getElementById("numA").value);
    const b = Number(document.getElementById("numB").value);

    try {
      const res = await fetch("/api/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ a, b })
      });

      const data = await res.json();
      if (data.error) {
        resultEl.textContent = "Error: " + data.error;
      } else {
        resultEl.textContent = "Result: " + data.result;
      }
    } catch (err) {
      resultEl.textContent = "Network error";
    }
  });
});
