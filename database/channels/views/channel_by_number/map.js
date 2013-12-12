function(doc){
    if(doc.type=="channel"){
        emit([doc.channel, doc.pass], [1]);
    }
}