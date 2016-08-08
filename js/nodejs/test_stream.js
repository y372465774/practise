var fs = require('fs');
var data = '';

var test_read = function(pt){

    var readStream = fs.createReadStream(pt);
    readStream.setEncoding('UTF8');
    
    // data : 
    // end :
    // error :
    
    readStream.on('data',function(chunk){
        console.log('chunk',chunk);
        data += chunk;
    });
    
    readStream.on('end',function(){
        console.log(data);
    });
    
    readStream.on('error',function(err){
        console.log(err.stack);
    });   
}

var test_write = function(pt){
    var writeStream = fs.createWriteStream(pt);

    writeStream.end();

    writeStream.on('finish',function(){
        console.log("写入完毕")
    });

}
