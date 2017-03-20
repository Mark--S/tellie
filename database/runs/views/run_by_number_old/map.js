function(doc){
    if(doc.type=="tellie_run"){
        emit(doc.run, [1]);
    }
}
