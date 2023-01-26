var express = require('express')
var router = express.Router()
const fetch=require('node-fetch');



router.get('/', function(req, res, next) {
    console.log('getPersonChores');
    
    var personId = req.query.personId;
    var personName = req.query.personName;
    // console.log(personId)
    var hostname = 'http://127.0.0.1';
    var port = ':5000';
    var person_chores_path='/api/v1/resources/get_person_chores';

    var url = hostname + port;
    fetch(url + person_chores_path + '?personId=' + personId, {
        method: 'POST',
        /* headers: {
            "Content-type": "application/x-www-form-urlencoded; charset=UTF-8"
        },
        body: 'personId=' + personId
        */
    })
    .then(response => response.json())
    .then(json => {
        var chore_list=json.results
        console.log("API response:", json)
        console.log("API response:", chore_list)
        res.render('showPersonChores', {title: 'Chore list for '+personName, chores: chore_list, personId: personId});
    })
    .catch(err => {
        console.log('Error message: ', err);
    });
});

module.exports = router;