// Load real data from extracted JSON files
let ALL_DATA = [];

async function loadData() {
  try {
    const res = await fetch("data/1911/records.json");
    if (!res.ok) throw new Error("Failed to load 1911 data");
    const data1911 = await res.json();
    ALL_DATA = data1911;
    console.log(`Loaded ${ALL_DATA.length} records`);
    render(ALL_DATA);
  } catch (e) {
    console.error(e);
    document.getElementById("resultCount").textContent = "שגיאה בטעינת הנתונים";
  }
}

function normalize(str) {
  return (str || "").toString().toLowerCase().trim();
}

function matches(record, filters) {
  if (filters.q) {
    const haystack = [
      record.surname, record.forename, record.birthplace,
      record.occupation, record.address, record.religion,
      record.familyRelationship, record.notes, record.nationality_or_notes
    ].map(normalize).join(" ");
    if (!haystack.includes(filters.q)) return false;
  }
  if (filters.year && String(record.year) !== filters.year) return false;
  if (filters.sex && record.sex !== filters.sex) return false;
  if (filters.surname && !normalize(record.surname).includes(filters.surname)) return false;
  if (filters.forename && !normalize(record.forename).includes(filters.forename)) return false;
  if (filters.birthplace && !normalize(record.birthplace).includes(filters.birthplace)) return false;
  if (filters.occupation && !normalize(record.occupation).includes(filters.occupation)) return false;
  if (filters.address && !normalize(record.address).includes(filters.address)) return false;
  return true;
}

function getFilters() {
  return {
    q: normalize(document.getElementById("q").value),
    year: document.getElementById("year").value,
    sex: document.getElementById("sex").value,
    surname: normalize(document.getElementById("surname").value),
    forename: normalize(document.getElementById("forename").value),
    birthplace: normalize(document.getElementById("birthplace").value),
    occupation: normalize(document.getElementById("occupation").value),
    address: normalize(document.getElementById("address").value)
  };
}

let currentResults = [];

function render(results) {
  currentResults = results;
  const tbody = document.querySelector("#results tbody");
  tbody.innerHTML = "";

  document.getElementById("resultCount").textContent =
    results.length === 0 ? "אין תוצאות" : `${results.length.toLocaleString()} תוצאות`;

  document.getElementById("exportCsv").disabled = results.length === 0;

  results.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.year || ""}</td>
      <td>${r.surname || ""}</td>
      <td>${r.forename || ""}</td>
      <td>${r.sex || ""}</td>
      <td>${r.age || ""}</td>
      <td>${r.birthplace || ""}</td>
      <td>${r.occupation || ""}</td>
      <td>${r.address || ""}</td>
      <td>${r.familyRelationship || ""}</td>
      <td>${r.religion || ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

function search() {
  const filters = getFilters();
  const results = ALL_DATA.filter(r => matches(r, filters));
  render(results);
}

function exportCsv() {
  if (!currentResults.length) return;
  const headers = ["year","id","surname","forename","sex","age","birthplace","religion","occupation","address","maritalStatus","familyRelationship","notes"];
  const rows = currentResults.map(r =>
    headers.map(h => `"${(r[h] || "").toString().replace(/"/g, '""')}"`).join(",")
  );
  const csv = ["\uFEFF" + headers.join(","), ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `gibraltar-census-export.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

document.getElementById("searchBtn").addEventListener("click", search);
document.getElementById("q").addEventListener("keydown", e => { if (e.key === "Enter") search(); });
document.getElementById("exportCsv").addEventListener("click", exportCsv);

// Load on start
loadData();
