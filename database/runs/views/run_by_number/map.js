function(doc){
    if(doc.type=="TELLIE_RUN"){
        emit(doc.run_range[0], doc.timestamp);
    }
}
