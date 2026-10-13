// Sample data from 1911 (will be replaced / extended with full extracted datasets)
const SAMPLE_DATA = [
  {
    year: 1911,
    id: "5811",
    surname: "(CHIVASCO)",
    forename: "Emilio",
    sex: "M",
    age: "16",
    birthplace: "Malaga",
    occupation: "read & write",
    address: "Civil Hospital Ramp",
    houseNo: "22B",
    maritalStatus: "Single",
    familyRelationship: "Son",
    religion: "Roman Catholic",
    notes: "British Subject"
  },
  {
    year: 1911,
    id: "example2",
    surname: "GARCIA",
    forename: "Maria",
    sex: "F",
    age: "34",
    birthplace: "Gibraltar",
    occupation: "At Home",
    address: "Main Street",
    houseNo: "45",
    maritalStatus: "Married",
    familyRelationship: "Wife",
    religion: "Roman Catholic",
    notes: ""
  },
  {
    year: 1911,
    id: "example3",
    surname: "COHEN",
    forename: "Isaac",
    sex: "M",
    age: "52",
    birthplace: "Gibraltar",
    occupation: "Merchant",
    address: "Irish Town",
    houseNo: "12",
    maritalStatus: "Married",
    familyRelationship: "Head",
    religion: "Jewish",
    notes: ""
  }
];

let currentResults = [];

function normalize(str) {
  return (str || "").toString().toLowerCase().trim();
}

function matches(record, filters) {
  if (filters.q) {
    const haystack = [
      record.surname, record.forename, record.birthplace,
      record.occupation, record.address, record.religion,
      record.familyRelationship, record.notes, record.houseNo
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
      <td>${[r.address, r.houseNo].filter(Boolean).join(" ")}</td>
      <td>${r.familyRelationship || ""}</td>
      <td>${r.religion || ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

function search() {
  const filters = getFilters();
  // In the future this will search across all loaded year datasets
  const results = SAMPLE_DATA.filter(r => matches(r, filters));
  render(results);
}

function exportCsv() {
  if (!currentResults.length) return;
  const headers = ["year","surname","forename","sex","age","birthplace","occupation","address","houseNo","maritalStatus","familyRelationship","religion","notes"];
  const rows = currentResults.map(r =>
    headers.map(h => `"${(r[h] || "").toString().replace(/"/g, '""')}"`).join(",")
  );
  const csv = [headers.join(","), ...rows].join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
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

// Initial render
render(SAMPLE_DATA);
