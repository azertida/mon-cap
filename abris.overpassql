/*
  Mon cap — récolte des abris candidats sur une commune.
  Testable tel quel sur https://overpass-turbo.eu (colle, puis "Exécuter").

  Astuce robustesse : à Bruxelles, le nom OSM des communes est bilingue
  (« Woluwe-Saint-Lambert - Sint-Lambrechts-Woluwe »), donc un filtre par nom
  simple échoue. On vise la relation directement par son identifiant :
     area(3600060167)->.zone;   // 60167 = relation OSM de WSL
*/

[out:json][timeout:25];

// --- Zone : Woluwe-Saint-Lambert ---
// On vise la commune par son identifiant de relation OSM (60167), insensible
// au nom bilingue bruxellois (« Woluwe-Saint-Lambert - Sint-Lambrechts-Woluwe »).
// Identifiant de zone = 3 600 000 000 + n° de relation.
area(3600060167)->.zone;

// --- Lieux candidats comme abris ---
(
  // pharmacies (horaires réguliers seulement ; la garde du dimanche est dynamique)
  nwr["amenity"="pharmacy"](area.zone);

  // bibliothèques, bâtiments communaux, centres communautaires
  nwr["amenity"="library"](area.zone);
  nwr["amenity"="townhall"](area.zone);
  nwr["amenity"="community_centre"](area.zone);

  // galeries / grands magasins (refuges climatisés, sièges, toilettes)
  nwr["shop"="mall"](area.zone);
  nwr["shop"="department_store"](area.zone);

  // lieux de culte (frais l'été SI ouverts — à vérifier sur le terrain)
  nwr["amenity"="place_of_worship"](area.zone);
);

// "center" renvoie un point unique pour les ways/relations (bâtiments)
out center tags;
