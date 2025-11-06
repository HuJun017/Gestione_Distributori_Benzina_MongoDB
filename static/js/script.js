// =====================
//     MAPPA
// =====================

const map = L.map("map").setView([41.9, 12.5], 6);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
	maxZoom: 19,
	attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

const markers = L.layerGroup().addTo(map);


// =====================
//     FUNZIONI
// =====================

function aggiornaMappa(data) {
	markers.clearLayers();
	if (!Array.isArray(data)) data = [data];

	data.forEach((d) => {
		const lat = d.lat;
		const lon = d.lon;
		if (!lat || !lon) return;

		const popup = `
			<b>${d.nome} (ID ${d.idDistributore ?? "n/a"})</b><br/>
			Provincia: ${d.provincia}<br/>
			Benzina: ${d.capienzaBenzina} L (€${d.prezzoBenzina})<br/>
			Diesel: ${d.capienzaDiesel} L (€${d.prezzoDiesel})<br/>
			Pompe: ${d.numeroPompe}
		`;

		L.marker([lat, lon])
			.addTo(markers)
			.bindPopup(popup);
	});

	if (data.length) {
		const coords = data
			.filter((d) => d.lat && d.lon)
			.map((d) => [d.lat, d.lon]);
		if (coords.length) map.fitBounds(L.latLngBounds(coords).pad(0.2));
	}
}


function generaElenco(data, containerId) {
	const container = document.getElementById(containerId);
	container.innerHTML = "";
	if (!Array.isArray(data)) data = [data];

	data.forEach((d) => {
		const el = document.createElement("div");
		el.className = "card p-2 mb-2";
		el.innerHTML = `
			<strong>${d.nome} (ID ${d.idDistributore ?? "n/a"})</strong><br/>
			Provincia: ${d.provincia}<br/>
			Benzina: ${d.capienzaBenzina} L (€${d.prezzoBenzina})<br/>
			Diesel: ${d.capienzaDiesel} L (€${d.prezzoDiesel})<br/>
			Pompe: ${d.numeroPompe}
		`;
		container.appendChild(el);
	});
}


async function safeFetch(url, options) {
	const res = await fetch(url, options);
	if (!res.ok) {
		const text = await res.text();
		throw new Error(text || `Errore ${res.status}`);
	}
	return await res.json();
}


// =====================
//     EVENTI
// =====================

// --- Elenco completo ---
let elencoVisibile = false;

document.getElementById("btn-list-all").addEventListener("click", async () => {
	const btn = document.getElementById("btn-list-all");
	const containerId = "list-all";

	if (elencoVisibile) {
		document.getElementById(containerId).innerHTML = "";
		markers.clearLayers();
		btn.innerText = "Mostra elenco";
		elencoVisibile = false;
		return;
	}

	try {
		let data = await safeFetch("/distributori");
		if (!data.length) alert("Nessun distributore trovato.");
		generaElenco(data, containerId);
		aggiornaMappa(data);
		btn.innerText = "Nascondi elenco";
		elencoVisibile = true;
	} catch (err) {
		alert("Errore nel recupero dei distributori: " + (err.message || err));
	}
});


// --- Ricerca per provincia ---
document.getElementById("btn-prov").addEventListener("click", async () => {
	const prov = document.getElementById("prov-input").value.trim();
	if (!prov) return alert("Inserisci una provincia");

	try {
		let data = await safeFetch(`/distributori/provincia/${encodeURIComponent(prov)}`);
		if (!data.length) {
			alert(`Nessun distributore trovato per la provincia: ${prov}`);
			return;
		}
		generaElenco(data, "prov-result");
		aggiornaMappa(data);
	} catch (err) {
		alert("Errore nella ricerca per provincia: " + (err.message || err));
	}
});


// --- Ricerca per ID ---
document.getElementById("btn-id").addEventListener("click", async () => {
	const id = document.getElementById("id-input").value;
	if (!id) return alert("Inserisci un ID");

	try {
		let data = await safeFetch(`/distributori/${id}`);
		data = Array.isArray(data) ? data : [data];
		generaElenco(data, "id-result");
		aggiornaMappa(data);
	} catch (err) {
		alert("Errore nella ricerca per ID: " + (err.message || err));
	}
});


// --- Cambio prezzo ---
document.getElementById("btn-change-price").addEventListener("click", async () => {
	const prov = document.getElementById("prov-price").value.trim();
	const tipo = document.getElementById("tipo-price").value;
	const nuovo = document.getElementById("new-price").value;
    console.log(prov, tipo, nuovo)

	if (!prov || !tipo || !nuovo) return alert("Compila tutti i campi");

	try {
		let data = await safeFetch(`/distributori/prezzo/${encodeURIComponent(prov)}`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				tipo: tipo,
				nuovo_prezzo: parseFloat(nuovo)
			})
		});
		generaElenco(data, "change-result");
		aggiornaMappa(data);
	} catch (err) {
		alert("Errore nell'aggiornamento prezzi: " + (err.message || err));
	}
});
