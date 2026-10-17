const CART_KEY = 'trattoria_cart';  // { "id": qty }

function getCart() {
  try { return JSON.parse(localStorage.getItem(CART_KEY)) || {}; }
  catch (e) { return {}; }
}
function saveCart(cart) {
  try { localStorage.setItem(CART_KEY, JSON.stringify(cart)); } catch (e) {}
  updateBadge();
}
function addToCart(id) {
  const cart = getCart();
  cart[id] = (cart[id] || 0) + 1;
  saveCart(cart);
}
function cartCount() {
  return Object.values(getCart()).reduce((a, b) => a + b, 0);
}
function updateBadge() {
  document.querySelectorAll('[data-cart-count]').forEach(el => el.textContent = cartCount());
}
updateBadge();
