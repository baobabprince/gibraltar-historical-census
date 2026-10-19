// Gibraltar Historical Census – frontend (loads slim multi-year data)
let ALL_DATA = [];
let currentResults = [];
let page = 0;
const PAGE_SIZE = 100;

const FILTER_IDS = [
  "q",
  "year",
  "sex",
  "surname",
  "forename",
  "birthplace",
  "occupation",
  "address",
  "religion",
  "marital",
  "relationship",
  "district",
  "ageMin",
  "ageMax",
];

function field(r, ...keys) {
  for (const k of keys) {
    if (r[k] != null && r[k] !== "") return r[k];
  }
  return "";
}

function addr(r) {
  const street = field(r, "street", "address", "streetName");
  const house = field(r, "houseNo", "houseno", "hseNo");
  if (street && house) return `${street} ${house}`;
  return street || house || "";
}

function parseAge(v) {
  if (v == null || v === "") return null;
  const n = parseInt(String(v).replace(/[^0-9]/g, ""), 10);
  return Number.isFinite(n) ? n : null;
}

async function loadData() {
  const countEl = document.getElementById("resultCount");
  countEl.textContent = "טוען נתונים...";
  try {
    let years = [];
    try {
      const idxRes = await fetch("data/index.json");
      if (idxRes.ok) {
        const idx = await idxRes.json();
        years = idx.years || [];
      }
    } catch (_) {}

    if (!years.length) {
      // Fallback: known complete years
      years = [1704, 1777, 1791, 1814, 1816, 1834, 1868, 1871, 1878, 1881, 1891, 1901, 1911, 1914].map(
        y => ({ year: y, file: `data/${y}/records.slim.json` })
      );
    }

    const loaded = [];
    for (const y of years) {
      const path = y.file || `data/${y.year}/records.slim.json`;
      try {
        const res = await fetch(path);
        if (!res.ok) {
          const full = await fetch(`data/${y.year}/records.json`);
          if (!full.ok) continue;
          const data = await full.json();
          loaded.push(...data);
          console.log(`Loaded ${data.length} from ${y.year} (full)`);
        } else {
          const data = await res.json();
          loaded.push(...data);
          console.log(`Loaded ${data.length} from ${y.year} (slim)`);
        }
      } catch (e) {
        console.warn("Skip year", y.year, e);
      }
    }

    ALL_DATA = loaded;
    if (!ALL_DATA.length) throw new Error("No data files found");

    const yearSelect = document.getElementById("year");
    const uniqueYears = [...new Set(ALL_DATA.map(r => r.year).filter(Boolean))].sort(
      (a, b) => a - b
    );
    yearSelect.innerHTML = '<option value="">כל השנים</option>';
    uniqueYears.forEach(y => {
      const opt = document.createElement("option");
      opt.value = y;
      opt.textContent = y;
      yearSelect.appendChild(opt);
    });

    render(ALL_DATA);
  } catch (e) {
    console.error(e);
    countEl.textContent = "שגיאה בטעינת הנתונים – נסה לרענן";
  }
}

function normalize(str) {
  return (str || "").toString().toLowerCase().trim();
}

function matches(record, filters) {
  if (filters.q) {
    const haystack = [
      field(record, "surname", "surName", "name"),
      field(record, "forename", "foreName"),
      field(record, "birthplace", "birthPlace"),
      field(record, "occupation"),
      addr(record),
      field(record, "religion", "nationality", "nationalityReligion"),
      field(record, "familyRelationship", "relationship"),
      field(record, "maritalStatus", "maritalstatus", "status"),
      field(record, "district"),
      field(record, "notes", "remarks"),
      field(record, "yearsOfResidence"),
    ]
      .map(normalize)
      .join(" ");
    if (!haystack.includes(filters.q)) return false;
  }

  if (filters.year && String(record.year) !== filters.year) return false;
  if (filters.sex && field(record, "sex") !== filters.sex) return false;

  if (
    filters.surname &&
    !normalize(field(record, "surname", "surName", "name")).includes(filters.surname)
  )
    return false;
  if (
    filters.forename &&
    !normalize(field(record, "forename", "foreName")).includes(filters.forename)
  )
    return false;
  if (
    filters.birthplace &&
    !normalize(field(record, "birthplace", "birthPlace")).includes(filters.birthplace)
  )
    return false;
  if (
    filters.occupation &&
    !normalize(field(record, "occupation")).includes(filters.occupation)
  )
    return false;
  if (filters.address && !normalize(addr(record)).includes(filters.address)) return false;

  if (
    filters.religion &&
    !normalize(
      field(record, "religion", "nationality", "nationalityReligion")
    ).includes(filters.religion)
  )
    return false;
  if (
    filters.marital &&
    !normalize(field(record, "maritalStatus", "maritalstatus", "status")).includes(
      filters.marital
    )
  )
    return false;
  if (
    filters.relationship &&
    !normalize(field(record, "familyRelationship", "relationship")).includes(
      filters.relationship
    )
  )
    return false;
  if (
    filters.district &&
    !normalize(field(record, "district")).includes(filters.district)
  )
    return false;

  if (filters.ageMin != null || filters.ageMax != null) {
    const age = parseAge(field(record, "age"));
    if (age == null) return false;
    if (filters.ageMin != null && age < filters.ageMin) return false;
    if (filters.ageMax != null && age > filters.ageMax) return false;
  }

  return true;
}

function getFilters() {
  const ageMinRaw = document.getElementById("ageMin").value;
  const ageMaxRaw = document.getElementById("ageMax").value;
  return {
    q: normalize(document.getElementById("q").value),
    year: document.getElementById("year").value,
    sex: document.getElementById("sex").value,
    surname: normalize(document.getElementById("surname").value),
    forename: normalize(document.getElementById("forename").value),
    birthplace: normalize(document.getElementById("birthplace").value),
    occupation: normalize(document.getElementById("occupation").value),
    address: normalize(document.getElementById("address").value),
    religion: normalize(document.getElementById("religion").value),
    marital: normalize(document.getElementById("marital").value),
    relationship: normalize(document.getElementById("relationship").value),
    district: normalize(document.getElementById("district").value),
    ageMin: ageMinRaw === "" ? null : parseInt(ageMinRaw, 10),
    ageMax: ageMaxRaw === "" ? null : parseInt(ageMaxRaw, 10),
  };
}

function clearFilters() {
  FILTER_IDS.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.tagName === "SELECT") el.selectedIndex = 0;
    else el.value = "";
  });
  render(ALL_DATA);
}

function render(results) {
  currentResults = results;
  page = 0;
  document.getElementById("resultCount").textContent =
    results.length === 0 ? "אין תוצאות" : `${results.length.toLocaleString()} תוצאות`;
  document.getElementById("exportCsv").disabled = results.length === 0;
  renderPage();
}

function renderPage() {
  const tbody = document.querySelector("#results tbody");
  tbody.innerHTML = "";
  const start = page * PAGE_SIZE;
  const slice = currentResults.slice(start, start + PAGE_SIZE);

  slice.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.year || ""}</td>
      <td>${field(r, "surname", "surName", "name")}</td>
      <td>${field(r, "forename", "foreName")}</td>
      <td>${field(r, "sex")}</td>
      <td>${field(r, "age")}</td>
      <td>${field(r, "birthplace", "birthPlace")}</td>
      <td>${field(r, "occupation")}</td>
      <td>${addr(r)}</td>
      <td>${field(r, "familyRelationship", "relationship")}</td>
      <td>${field(r, "religion", "nationality", "nationalityReligion")}</td>
      <td>${field(r, "maritalStatus", "maritalstatus", "status")}</td>
      <td>${field(r, "district")}</td>
    `;
    tbody.appendChild(tr);
  });

  let pager = document.getElementById("pager");
  if (!pager) {
    pager = document.createElement("div");
    pager.id = "pager";
    pager.className = "pager";
    document.querySelector(".table-wrapper").after(pager);
  }
  const totalPages = Math.max(1, Math.ceil(currentResults.length / PAGE_SIZE));
  pager.innerHTML = "";
  if (currentResults.length > PAGE_SIZE) {
    const prev = document.createElement("button");
    prev.textContent = "הקודם";
    prev.className = "secondary";
    prev.type = "button";
    prev.disabled = page === 0;
    prev.onclick = () => {
      page--;
      renderPage();
      window.scrollTo({
        top: document.querySelector(".table-wrapper").offsetTop - 20,
        behavior: "smooth",
      });
    };
    const info = document.createElement("span");
    info.textContent = ` עמוד ${page + 1} מתוך ${totalPages} `;
    const next = document.createElement("button");
    next.textContent = "הבא";
    next.className = "secondary";
    next.type = "button";
    next.disabled = page >= totalPages - 1;
    next.onclick = () => {
      page++;
      renderPage();
      window.scrollTo({
        top: document.querySelector(".table-wrapper").offsetTop - 20,
        behavior: "smooth",
      });
    };
    pager.append(prev, info, next);
  }
}

function search() {
  const filters = getFilters();
  const results = ALL_DATA.filter(r => matches(r, filters));
  render(results);
}

function exportCsv() {
  if (!currentResults.length) return;
  const headers = [
    "year",
    "id",
    "surname",
    "forename",
    "sex",
    "age",
    "birthplace",
    "occupation",
    "street",
    "houseNo",
    "familyRelationship",
    "religion",
    "maritalStatus",
    "district",
    "yearsOfResidence",
    "notes",
  ];
  const rows = currentResults.map(r =>
    headers
      .map(h => {
        let v;
        if (h === "street") v = field(r, "street", "address");
        else v = field(r, h);
        return `"${(v || "").toString().replace(/"/g, '""')}"`;
      })
      .join(",")
  );
  const csv = ["\uFEFF" + headers.join(","), ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "gibraltar-census-export.csv";
  a.click();
  URL.revokeObjectURL(url);
}

document.getElementById("searchBtn").addEventListener("click", search);
document.getElementById("clearBtn").addEventListener("click", clearFilters);
document.getElementById("exportCsv").addEventListener("click", exportCsv);

FILTER_IDS.forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("keydown", e => {
    if (e.key === "Enter") search();
  });
});

// Auto-search when year/sex dropdown changes
["year", "sex"].forEach(id => {
  document.getElementById(id).addEventListener("change", search);
});

loadData();
