var express = require('express')
var router = express.Router()
const fetch=require('node-fetch');



router.get('/', function(req, res, next) {
    console.log('showPersonChores');
    res.render('showPersonChores', {title: title, chores: chores});
});

module.exports = router;