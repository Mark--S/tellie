function (doc) {/*Do not change this function as Orca is dependent upon this*/
		if(doc.type == "fire_parameters"){
				emit(doc.last_valid, doc);
		}
}