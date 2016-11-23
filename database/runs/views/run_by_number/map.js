function(doc){
    if(doc.type=="TELLIE_RUN"){
        emit(doc.run, doc.timestamp);
    }
}
