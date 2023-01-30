var express = require('express')
var router = express.Router()
const fetch=require('node-fetch');



router.get('/', function(req, res, next) {
    console.log('createChore');
    res.render('createChore', {title: 'Create new chore'});
});

module.exports = router;