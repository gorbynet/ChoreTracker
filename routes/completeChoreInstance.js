var express = require('express')
var router = express.Router()
const fetch=require('node-fetch');



router.get('/', function(req, res, next) {
    console.log('completeChoreInstance');
    var choreInstanceId = req.query.choreInstanceId;
    var personId = req.query.personId;
    console.log('choreInstanceId', choreInstanceId)
    console.log('personId', personId)
    var hostname = 'http://127.0.0.1';
    var port = ':5000';
    var complete_chore_path='/api/v1/resources/complete_chore_instance';

    var url = hostname + port;
    fetch(url + complete_chore_path + '?choreInstanceId=' + choreInstanceId + '&personId=' + personId, {
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
        // res.render('showPersonChores', {title: 'Chore list for '+personName, chores: chore_list});
    })
    .catch(err => {
        console.log('Error message: ', err);
    });
});

module.exports = router;