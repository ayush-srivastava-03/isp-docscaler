package deployment

import "isp/config"

var DARKSITE_DEPLOYMENT = config.GetBool("DARKSITE_DEPLOYMENT", false)

func IsDarkSite() bool {
	return DARKSITE_DEPLOYMENT
}
