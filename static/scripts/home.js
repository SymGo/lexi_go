async function sendText() {
    // ON RÉCUPÈRE LES VARIABLES À ENVOYER AU SERVEUR
    var inText = document.getElementById('inText').value;

    // ON EMBALLE NOTRE VARIABLE DANS UN DICTIONNAIRE
    // ON PEUT ENVOYER AUTANT DE VARIABLES QU'ON VEUT, ICI ON SE CONTENTE D'ENVOYER inText
    var colis = {
        inText: inText
    }
    console.log('Envoi colis:', colis);

    // PARAMÈTRES DE LA REQUÊTE
    const requete = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(colis)
    };

    // ENVOI ET RÉCUPÉRATION DE LA RÉPONSE
    const response = await fetch('/analyze/', requete)
    const data = await response.json();
    console.log(data);

    var outText = document.getElementById('outText');
    outText.innerHTML = ""; // vider la div si elle contenait déjà qqc
    for (token in data.reponse) {
        var tokenTuple = data.reponse[token];
        console.log(tokenTuple[0], tokenTuple[1]);
        outText.innerHTML += tokenTuple[0] + ' : ' + tokenTuple[1] + '<br/>';
    }
}