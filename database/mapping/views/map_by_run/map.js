function(doc){
    if(doc.type=="mapping"){
        emit([doc.run_range, doc.pass], [1]);
    }
}
