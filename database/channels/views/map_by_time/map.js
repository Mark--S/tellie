function(doc){
    if(doc.type=="mapping"){
        emit([doc.index, doc.timestamp, doc.pass], [1]);
    }
}
