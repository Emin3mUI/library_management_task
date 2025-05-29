// /static/js/index.js

// Load books from backend and render table + dropdowns
async function loadAndRender() {
  try {
    const resp  = await fetch('/books');
    const books = await resp.json();

    const table        = document.getElementById('book-table');
    const borrowSelect = document.getElementById('borrowBookId');
    const returnSelect = document.getElementById('returnBookId');

    // Clear old content
    table.innerHTML        = '';
    borrowSelect.innerHTML = '<option value="">Select a Book</option>';
    returnSelect.innerHTML = '<option value="">Select a Book</option>';

    books.forEach(b => {
      const tr = document.createElement('tr');
      tr.dataset.id = b.book_id;
      const state = b.available ? 'Present' : 'Borrowed';

      tr.innerHTML = `
        <td>${b.book_id}</td>
        <td>${b.title}</td>
        <td>${b.author}</td>
        <td>${b.publisher || ''}</td>
        <td>${b.genre    || ''}</td>
        <td>${state === 'Borrowed' ? '—' : ''}</td>
        <td>${state === 'Borrowed' ? '—' : ''}</td>
        <td>${state === 'Borrowed' ? '—' : ''}</td>
        <td>${state}</td>
      `;
      table.appendChild(tr);

      // Populate dropdowns
      const opt = document.createElement('option');
      opt.value = b.book_id;
      opt.textContent = `${b.book_id} — ${b.title}`;
      if (b.available) borrowSelect.appendChild(opt);
      else            returnSelect.appendChild(opt);
    });
  } catch (err) {
    console.error('Error loading books:', err);
    alert('Failed to load book data.');
  }
}

// Initial load
window.addEventListener('DOMContentLoaded', loadAndRender);

// Borrow Book
document.getElementById('borrowForm').addEventListener('submit', async e => {
  e.preventDefault();
  const book_id        = document.getElementById('borrowBookId').value;
  const borrower_email = document.getElementById('borrowerName').value.trim();
  const start_date     = document.getElementById('borrowDate').value;
  // For now we use the same date as return_date
  const return_date    = start_date;

  if (!book_id || !borrower_email || !start_date) {
    return alert('Please fill in all fields.');
  }
  if (!confirm(`Borrow book ${book_id}?`)) return;

  try {
    const resp = await fetch('/borrow', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ book_id, borrower_email, start_date, return_date })
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error||'Borrow failed');
    alert(data.message);
    await loadAndRender();
  } catch (err) {
    alert(err.message);
  }
});

// Return Book
document.getElementById('returnForm').addEventListener('submit', async e => {
  e.preventDefault();
  const book_id    = document.getElementById('returnBookId').value;
  const return_date = document.getElementById('returnDate').value;

  if (!book_id || !return_date) {
    return alert('Please fill in all fields.');
  }
  if (!confirm(`Return book ${book_id}?`)) return;

  try {
    const resp = await fetch('/return', {
      method: 'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ book_id, return_date })
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error||'Return failed');
    alert(data.message);
    await loadAndRender();
  } catch (err) {
    alert(err.message);
  }
});

// Clear All Borrowing Data
document.getElementById('clearDataBtn').addEventListener('click', async () => {
  if (!confirm('Clear all borrowing data?')) return;
  try {
    const resp = await fetch('/clear-borrowings',{ method:'POST' });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error||'Clear failed');
    alert(data.message);
    await loadAndRender();
  } catch (err) {
    alert(err.message);
  }
});
