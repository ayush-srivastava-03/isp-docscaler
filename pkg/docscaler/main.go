package docscaler

import "strconv"

type Config struct {
	General struct {
		Date         string      `json_name:"date"`
		DocumentName string      `json_name:"document_name"`
		Title        NumericList `json_name:"title"`
	} `json_name:"general"`

	Customer struct {
		Company string      `json_name:"company"`
		Name    string      `json_name:"name"`
		Phone   string      `json_name:"phone"`
		Email   string      `json_name:"email"`
		Address NumericList `json_name:"address"`
	} `json_name:"customer"`

	DDN struct {
		Team []struct {
			Name       string `json_name:"name"`
			Role       string `json_name:"role"`
			Phone      string `json_name:"phone"`
			Email      string `json_name:"email"`
			DocCreator string `json_name:"doc_creator"`
		} `json_name:"team"`
	} `json_name:"ddn"`

	Network struct {
		RackDiagram string `json_name:"rack_diagram"`
	} `json_name:"network"`

	Project struct {
		// ???
		// "home": {
		// 	"sfa": [
		// 	   "sss_home.tgz"
		// 	],
		// 	"lustre": "es_showall_home_tud.tgz"
		//  },
		//  "scratch": {
		// 	"sfa": [
		// 	   "sss_scratch.tgz"
		// 	],
		// 	"lustre": "es_showall_scratch_tud.tgz"
		//  }
	} `json_name:"project"`

	Templates []string `json_name:"templates"`
}

type NumericList map[string]string

func ArrayAsNumericList(src []string) NumericList {
	res := NumericList{}
	for i, v := range src {
		res[strconv.Itoa(i+1)] = v
	}

	return res
}
