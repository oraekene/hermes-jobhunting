// pricing.js — checkout flow
// Server decides market from cf-ipcountry. Client sends only email + skus.

const WORKER = "https://hermes-licensing.solarsizer.workers.dev";

// Display prices based on visitor's region (detected by Cloudflare)
async function loadPrices() {
  try {
    const r = await fetch(`${WORKER}/v1/checkout`, {
      method: "OPTIONS",
      headers: { "origin": location.origin },
    });
    // We can't read cf-ipcountry from JS, so show both and let server decide
    document.querySelectorAll('[data-sku="base"]').forEach(el => {
      el.textContent = "From $100 / ₦35,000";
    });
    document.querySelectorAll('[data-sku="addon"]').forEach(el => {
      el.textContent = "From $30 / ₦25,000 each";
    });
  } catch {
    // Worker might be down — show defaults
    document.querySelectorAll('[data-sku="base"]').forEach(el => {
      el.textContent = "$100 / ₦35,000";
    });
    document.querySelectorAll('[data-sku="addon"]').forEach(el => {
      el.textContent = "$30 / ₦25,000 each";
    });
  }
}

// Handle buy button clicks
document.querySelectorAll(".buy-btn").forEach(btn => {
  btn.addEventListener("click", async () => {
    const sku = btn.dataset.sku;
    const email = prompt("Enter your email address:");
    if (!email) return;

    btn.disabled = true;
    btn.textContent = "Redirecting...";

    try {
      const r = await fetch(`${WORKER}/v1/checkout`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, skus: [sku] }),
      });
      const data = await r.json();

      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        alert(data.error || "Checkout failed. Please try again.");
        btn.disabled = false;
        btn.textContent = `Buy ${sku === "base" ? "Core" : "Addon"}`;
      }
    } catch (err) {
      alert("Network error. Please try again.");
      btn.disabled = false;
      btn.textContent = `Buy ${sku === "base" ? "Core" : "Addon"}`;
    }
  });
});

loadPrices();
