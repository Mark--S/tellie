function(doc){
    if(doc.type=="run"){
        emit(doc.run, [1]);
    }
}