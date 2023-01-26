var express = require('express');
var router = express.Router();
const fetch=require('node-fetch');

router.get('/', function(req, res, next) {
    console.log('index');
    var hostname = 'http://127.0.0.1';
    var port = ':5000';
    var person_chores_path='/api/v1/resources/get_chore_counts_by_person';

    var url = hostname + port;
    fetch(url + person_chores_path, {
        method: 'POST',
        /* headers: {
            "Content-type": "application/x-www-form-urlencoded; charset=UTF-8"
        },
        body: 'personId=' + personId
        */
    })
    .then(response => response.json())
    .then(json => {
        var people=json.results
        
        // const people = []
        console.log("API response:", people)
        /*
        for (var person in chore_list) {
            console.log(person, chore_list[person]['PersonName'])
            people.push([person, chore_list[person]['PersonName'], chore_list[person]['ChoreCount']])
        }
        */
        res.render('index', {title: 'ChoreTracker', people: people});
    })
    /*
    res.render('index', {title: 'ChoreTracker', people:[
        [5, 'Lottie', 1],
        [1, 'Mike', 2]
    ]});
    */
});

/*
router.post('/', function(req, res, next) {
    res.render('index', {title: 'ChoreTracker'});
});
*/

module.exports = router;
