/* Formulaire de demande de diagnostic : vérification des champs, puis ouverture de la messagerie
   du visiteur avec la demande déjà rédigée. Le message reste affiché, prêt à copier, si aucune
   messagerie ne s'ouvre. La réponse se fait par e-mail. */
(function () {
  "use strict";

  var form = document.getElementById("form-devis");
  if (!form) return;

  // Adresse de destination encodée dans la page (texte inversé, puis base64), comme dans site.js.
  function adresseDestinataire() {
    try {
      var binaire = atob(form.getAttribute("data-courriel") || "");
      var octets = new Uint8Array(binaire.length);
      for (var i = 0; i < binaire.length; i++) octets[i] = binaire.charCodeAt(i);
      return new TextDecoder().decode(octets).split("").reverse().join("");
    } catch (e) {
      return "";
    }
  }
  var etat = form.querySelector("[data-etat-envoi]");

  // Demande choisie depuis une autre page : devis.html?demande=diagnostic, question ou suivi.
  var demandes = { diagnostic: "Diagnostic à domicile", question: "Une question d’abord", suivi: "Suivi ou réglage" };
  var demandee = new URLSearchParams(window.location.search).get("demande");
  if (demandee && demandes[demandee]) {
    var radio = form.querySelector('input[name="demande"][value="' + demandes[demandee] + '"]');
    if (radio) radio.checked = true;
  }

  function valeur(nom) {
    var champ = form.elements[nom];
    return champ && typeof champ.value === "string" ? champ.value.trim() : "";
  }

  function choix(nom) {
    var coche = form.querySelector('input[name="' + nom + '"]:checked');
    return coche ? coche.value : "";
  }

  function cochees(nom) {
    return Array.prototype.map.call(form.querySelectorAll('input[name="' + nom + '"]:checked'), function (c) {
      return c.value;
    });
  }

  function signaler(nom, texte) {
    var champ = form.elements[nom];
    var zone = form.querySelector('[data-erreur-pour="' + nom + '"]');
    if (zone) zone.textContent = texte || "";
    if (champ) {
      if (texte) champ.setAttribute("aria-invalid", "true");
      else champ.removeAttribute("aria-invalid");
    }
  }

  function verifier() {
    ["prenom", "commune", "courriel"].forEach(function (n) { signaler(n, ""); });
    var premier = null;
    var noter = function (nom, texte) {
      signaler(nom, texte);
      if (!premier) premier = nom;
    };
    var courriel = valeur("courriel");
    if (!valeur("prenom")) noter("prenom", "Indiquez votre prénom.");
    if (!valeur("commune")) noter("commune", "Indiquez votre commune ou votre arrondissement.");
    if (!courriel) noter("courriel", "Indiquez votre adresse e-mail pour que je puisse vous répondre.");
    else if (form.elements.courriel.validity.typeMismatch || /\.\.|^\.|\.@/.test(courriel) || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(courriel)) {
      noter("courriel", "Cette adresse e-mail semble incorrecte : vérifiez qu’elle est complète, sans accent ni espace.");
    }
    if (premier) form.elements[premier].focus();
    return !premier;
  }

  var phrases = {
    "Diagnostic à domicile": "Je souhaite un diagnostic à domicile.",
    "Une question d’abord": "J’ai d’abord une question.",
    "Suivi ou réglage": "Je vous écris pour le suivi ou un réglage de mon installation."
  };

  function texteDemande() {
    var l = [];
    var destinataire = form.getAttribute("data-prenom-destinataire");
    l.push("Bonjour" + (destinataire ? " " + destinataire : "") + ",");
    l.push("");
    l.push(phrases[choix("demande")] || "Je vous écris au sujet de la domotique.");
    l.push("");
    l.push("Commune : " + valeur("commune"));
    if (choix("logement")) l.push("Logement : " + choix("logement"));
    var objets = cochees("objets");
    if (objets.length) l.push("Ce que j’ai déjà : " + objets.join(", "));
    var usages = cochees("usages");
    if (usages.length) l.push("Ce qui m’intéresse : " + usages.join(", "));
    if (valeur("message")) {
      l.push("");
      l.push(valeur("message"));
    }
    l.push("");
    l.push("Prénom : " + valeur("prenom"));
    l.push("Mon adresse e-mail : " + valeur("courriel"));
    return l.join("\n");
  }

  function sujet() {
    var d = choix("demande");
    if (d === "Une question d’abord") return "Question";
    if (d === "Suivi ou réglage") return "Suivi ou réglage";
    return "Demande de diagnostic";
  }

  function lienMessagerie() {
    return "mailto:" + adresseDestinataire() +
      "?subject=" + encodeURIComponent(sujet()) +
      "&body=" + encodeURIComponent(texteDemande());
  }

  function copier(texte, bouton, zone) {
    var fini = function (ok) {
      bouton.textContent = ok ? "Message copié" : "Copie impossible : sélectionnez le texte";
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(texte).then(function () { fini(true); }, function () { fini(false); });
    } else {
      zone.select();
      try { fini(document.execCommand("copy")); } catch (e) { fini(false); }
    }
  }

  function boite(titre, paragraphe) {
    etat.textContent = "";
    var div = document.createElement("div");
    div.className = "boite-envoi";
    var h = document.createElement("h3");
    h.textContent = titre;
    var p = document.createElement("p");
    p.textContent = paragraphe;
    var zone = document.createElement("textarea");
    zone.readOnly = true;
    zone.value = texteDemande();
    zone.setAttribute("aria-label", "Votre demande, prête à copier");
    var actions = document.createElement("div");
    actions.className = "actions";
    var ouvrir = document.createElement("a");
    ouvrir.className = "bouton bouton-petit";
    ouvrir.href = lienMessagerie();
    ouvrir.textContent = "Ouvrir ma messagerie";
    var bCopier = document.createElement("button");
    bCopier.type = "button";
    bCopier.className = "bouton bouton-second bouton-petit";
    bCopier.textContent = "Copier le message";
    bCopier.addEventListener("click", function () { copier(zone.value, bCopier, zone); });
    actions.appendChild(ouvrir);
    actions.appendChild(bCopier);
    div.appendChild(h);
    div.appendChild(p);
    div.appendChild(zone);
    div.appendChild(actions);
    etat.appendChild(div);
    h.setAttribute("tabindex", "-1");
    h.focus();
  }

  function ouvrirMessagerie() {
    boite("Votre messagerie s’ouvre avec la demande déjà rédigée",
      "Il vous reste à l’envoyer. Si rien ne s’ouvre, copiez le message ci-dessous et envoyez-le à " +
      adresseDestinataire() + ".");
    window.location.href = lienMessagerie();
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (verifier()) ouvrirMessagerie();
  });

  ["prenom", "commune", "courriel"].forEach(function (nom) {
    var champ = form.elements[nom];
    if (champ) champ.addEventListener("input", function () {
      if (champ.getAttribute("aria-invalid") === "true") signaler(nom, "");
    });
  });
})();
