var express = require('express')
var router = express.Router()
const fetch=require('node-fetch');



router.get('/', function(req, res, next) {
    console.log('uncompleteChoreInstance');
    var choreInstanceId = req.query.choreInstanceId;
    console.log('choreInstanceId', choreInstanceId)
    var hostname = 'http://127.0.0.1';
    var port = ':5000';
    var complete_chore_path='/api/v1/resources/uncomplete_chore_instance';

    var url = hostname + port;
    fetch(url + complete_chore_path + '?choreInstanceId=' + choreInstanceId, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(json => {
        var chore_list=json.results
        console.log("API response:", json)
        console.log("API response:", chore_list)
        res.render('index', {title: 'ChoreTracker'});
    })
    .catch(err => {
        console.log('Error message: ', err);
    });
});

module.exports = router;