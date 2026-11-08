/* Comportements communs à toutes les pages : coordonnées, en-tête, menu mobile, barre d'action mobile. */
(function () {
  "use strict";

  // Coordonnées : absentes du code HTML pour les robots qui les y cherchent (voir outils/construire.py).
  function decoder(code) {
    try {
      var binaire = atob(code);
      var octets = new Uint8Array(binaire.length);
      for (var i = 0; i < binaire.length; i++) octets[i] = binaire.charCodeAt(i);
      return new TextDecoder().decode(octets).split("").reverse().join("");
    } catch (e) {
      return "";
    }
  }
  document.querySelectorAll("[data-lien]").forEach(function (a) {
    var lien = decoder(a.getAttribute("data-lien"));
    if (lien) {
      a.setAttribute("href", lien);
      a.removeAttribute("data-lien");
    }
  });
  document.querySelectorAll(".cm").forEach(function (s) {
    var texte = s.getAttribute("data-a") + (s.classList.contains("cm-arobase") ? "@" : "") + s.getAttribute("data-b");
    s.replaceWith(document.createTextNode(texte));
  });

  // En-tête : un filet apparaît dès que la page défile.
  var entete = document.querySelector("[data-entete]");
  function surDefilement() {
    if (entete) entete.classList.toggle("est-defile", window.scrollY > 8);
  }
  window.addEventListener("scroll", surDefilement, { passive: true });
  surDefilement();

  // Menu mobile.
  var bouton = document.querySelector("[data-menu-bouton]");
  var menu = document.getElementById("menu");
  if (bouton && menu) {
    var fermer = function () {
      bouton.setAttribute("aria-expanded", "false");
      menu.classList.remove("est-ouvert");
    };
    bouton.addEventListener("click", function () {
      var ouvert = bouton.getAttribute("aria-expanded") === "true";
      bouton.setAttribute("aria-expanded", String(!ouvert));
      menu.classList.toggle("est-ouvert", !ouvert);
      // Le menu est placé avant le bouton dans la page : on y amène le focus.
      if (!ouvert) menu.querySelector("a").focus();
    });
    // Quand le focus quitte l’en-tête (touche Tab), le menu se referme.
    document.addEventListener("focusin", function (e) {
      if (menu.classList.contains("est-ouvert") && !e.target.closest("[data-entete]")) fermer();
    });
    menu.addEventListener("click", function (e) {
      if (e.target.closest("a")) fermer();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.classList.contains("est-ouvert")) {
        fermer();
        bouton.focus();
      }
    });
    document.addEventListener("click", function (e) {
      if (!menu.contains(e.target) && !bouton.contains(e.target)) fermer();
    });
    var large = window.matchMedia("(min-width: 921px)");
    if (large.addEventListener) large.addEventListener("change", fermer);
  }

  // Barre d'action fixe sur mobile : visible une fois le haut de page dépassé,
  // cachée quand l'appel final ou le pied de page sont à l'écran.
  var barre = document.querySelector("[data-barre-mobile]");
  if (barre && "IntersectionObserver" in window) {
    var ouverture = document.querySelector("[data-haut]");
    var apresOuverture = !ouverture;
    var finsVisibles = new Set();
    var maj = function () {
      var visible = apresOuverture && finsVisibles.size === 0;
      barre.classList.toggle("est-visible", visible);
      barre.inert = !visible;
      barre.setAttribute("aria-hidden", String(!visible));
    };
    if (ouverture) {
      new IntersectionObserver(function (entrees) {
        apresOuverture = !entrees[0].isIntersecting;
        maj();
      }, { rootMargin: "-120px 0px 0px 0px" }).observe(ouverture);
    }
    var obs = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (e.isIntersecting) finsVisibles.add(e.target);
        else finsVisibles.delete(e.target);
      });
      maj();
    });
    document.querySelectorAll("[data-appel-final], .pied").forEach(function (el) { obs.observe(el); });
    maj();
  }
})();
