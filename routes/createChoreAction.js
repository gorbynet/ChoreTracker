var express = require('express')
var router = express.Router()
const fetch=require('node-fetch');



router.post('/', function(req, res, next) {
    console.log('createChoreAction');
    console.log("Request body: %j", req.body)
    var hostname = 'http://127.0.0.1';
    var port = ':5000';
    var create_chore_path='/api/v1/resources/create_chore';
    var personId = 4;
    var url = hostname + port;
    var data='';
    for (field in req.body) {
        if (data.length > 0) {
            data = data + '&'
        }
        data=data + encodeURIComponent(field) + '=' + encodeURIComponent(req.body[field])
    }
    fetch(url + create_chore_path, {
        method: 'POST',
        headers: {
            "Content-type": "application/x-www-form-urlencoded; charset=UTF-8"
        },
        body: data
        

    })
    .then(response => response.json())
    .then(json => {
        if (json.results['results'] = true) {
            res.redirect('/');
        }
    })
    .catch(err => {
        console.log('Error message: ', err);
    });
});

module.exports = router;