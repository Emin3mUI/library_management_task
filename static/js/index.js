// static/js/index.js

// ---------------------------------------------------
// 1) Fetch & render the book list (table + dropdowns)
// ---------------------------------------------------
async function loadAndRender() {
  const table        = document.getElementById('book-table');
  const borrowSelect = document.getElementById('borrowBookId');
  const returnSelect = document.getElementById('returnBookId');

  // Clear any existing rows / options
  table.innerHTML        = '';
  borrowSelect.innerHTML = '<option value="">Select a Book</option>';
  returnSelect.innerHTML = '<option value="">Select a Book</option>';

  try {
    const resp = await fetch('/books');
    console.log('GET /books status:', resp.status, 'content-type:', resp.headers.get('content-type'));
    const text = await resp.text();
    console.log('GET /books body:', text);

    if (!resp.ok) {
      throw new Error(`Server returned ${resp.status}`);
    }

    let books;
    try {
      books = JSON.parse(text);
    } catch {
      throw new Error('Invalid JSON from /books');
    }

    // For each book, append a row and decide which dropdown it belongs in
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

      // Build a <option> for this book
      const opt = document.createElement('option');
      opt.value       = b.book_id;
      opt.textContent = `${b.book_id} — ${b.title}`;

      if (b.available) {
        // Only available books go into the “Borrow” dropdown
        borrowSelect.appendChild(opt);
      } else {
        // Already‐borrowed books go into the “Return” dropdown
        returnSelect.appendChild(opt);
      }
    });
  } catch (err) {
    console.error('loadAndRender error:', err);
    alert(`Failed to load book data: ${err.message}`);
  }
}

// ---------------------------------------------------
// 2) Utility: Attempt JSON.parse, otherwise show raw
// ---------------------------------------------------
async function parseJsonOrThrow(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(text || `HTTP ${response.status}`);
  }
}

// ---------------------------------------------------
// 3) Handle “Borrow Book” form submission
// ---------------------------------------------------
async function handleBorrow(event) {
  event.preventDefault();

  const book_id        = document.getElementById('borrowBookId').value;
  const borrower_email = document.getElementById('borrowerName').value.trim();
  const start_date     = document.getElementById('borrowDate').value;
  const return_date    = start_date; // Or edit if you want a separate field

  // 3.1) Basic validation
  if (!book_id || !borrower_email || !start_date) {
    return alert('Please fill in all fields before borrowing.');
  }
  if (!confirm(`Borrow book ${book_id}?`)) {
    return;
  }

  try {
    const resp = await fetch('/borrow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ book_id, borrower_email, start_date, return_date })
    });
    const data = await parseJsonOrThrow(resp);
    if (!resp.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    alert(data.message);
    await loadAndRender();
    // Clear the form fields
    document.getElementById('borrowForm').reset();
  } catch (err) {
    console.error('Borrow error:', err);
    alert(`Borrow failed: ${err.message}`);
  }
}

// ---------------------------------------------------
// 4) Handle “Return Book” form submission
// ---------------------------------------------------
async function handleReturn(event) {
  event.preventDefault();

  const book_id    = document.getElementById('returnBookId').value;
  const return_date = document.getElementById('returnDate').value;

  // 4.1) Basic validation
  if (!book_id || !return_date) {
    return alert('Please select a book and enter a return date.');
  }
  if (!confirm(`Return book ${book_id}?`)) {
    return;
  }

  try {
    const resp = await fetch('/return', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ book_id, return_date })
    });
    const data = await parseJsonOrThrow(resp);
    if (!resp.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    alert(data.message);
    await loadAndRender();
    // Clear the return form fields
    document.getElementById('returnForm').reset();
  } catch (err) {
    console.error('Return error:', err);
    alert(`Return failed: ${err.message}`);
  }
}

// ---------------------------------------------------
// 5) Handle “Clear All Borrowing Data” button click
// ---------------------------------------------------
async function handleClear(event) {
  event.preventDefault();

  if (!confirm('Clear all borrowing data? This cannot be undone.')) {
    return;
  }

  try {
    const resp = await fetch('/clear-borrowings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}' // send an empty JSON object so it isn’t a truly empty payload
    });
    const data = await parseJsonOrThrow(resp);
    if (!resp.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    alert(data.message);
    await loadAndRender();
  } catch (err) {
    console.error('Clear error:', err);
    alert(`Clear failed: ${err.message}`);
  }
}

// ---------------------------------------------------
// 6) Wire everything up when DOM is ready
// ---------------------------------------------------
window.addEventListener('DOMContentLoaded', () => {
  // Initially fetch and render the table & dropdowns
  loadAndRender();

  // Hook up Borrow button
  const borrowForm = document.getElementById('borrowForm');
  borrowForm.addEventListener('submit', handleBorrow);

  // Hook up Return button
  const returnForm = document.getElementById('returnForm');
  returnForm.addEventListener('submit', handleReturn);

  // Hook up Clear All Borrowing Data button
  const clearBtn = document.getElementById('clearDataBtn');
  clearBtn.addEventListener('click', handleClear);
});
