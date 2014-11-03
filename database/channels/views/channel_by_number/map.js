function(doc){
    if(doc.type=="CHANNEL"){
        emit([doc.CHANNEL, doc.timestamp, doc.pass], [1]);
    }
}
