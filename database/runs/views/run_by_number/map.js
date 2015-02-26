function(doc){
    if(doc.type=="RUN"){
        emit(doc.run, [1]);
    }
}
