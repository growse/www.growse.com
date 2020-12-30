package main

import (
	"fmt"
	"github.com/gin-contrib/location"
	"github.com/gin-contrib/static"
	"github.com/gin-gonic/gin"
	_ "time"
)

const (
	owntracksFrontendConfig = `var yesterday = new Date(new Date().getTime() - (24 * 60 * 60 * 1000));
window.owntracks = window.owntracks || {};
window.owntracks.config = {
  api: {
       baseUrl: "%s",
       fetchOptions: { credentials: "include" }
  },
  map: {
       center: {
         lat: 53.67,
         lng: -1.58
       }
  },
  startDateTime: yesterday,
  verbose: true,
  router: {
    basePath: "%s",
  },
};`
)

func BuildRoutes(router *gin.Engine) {
	router.Use(location.New(location.Config{Scheme: "http", Host: "localhost", Base: "/where/data"}))
	router.Use(static.ServeRoot("/where/ui/", configuration.OwntracksFrontendDir))
	authorized := router.Group("/where/")
	authorized.Use(AuthRequired())
	{
		//authorized.GET("", func(c *gin.Context) {
		//	c.Redirect(301, "/where/ui/")
		//})
		authorized.GET("ui/config/config.js", func(c *gin.Context) {
			fmt.Printf("API location: %v\n", location.Get(c))
			c.String(200, owntracksFrontendConfig, location.Get(c), location.Get(c).Path)
		})

		otRecorderAPI := authorized.Group("data")
		{
			restAPI := otRecorderAPI.Group("api/0")
			{
				restAPI.GET("list", OTListUserHandler)
				restAPI.GET("last", OTLastPosHandler)
				restAPI.GET("locations", OTLocationsHandler)
				restAPI.GET("version", OTVersionHandler)
			}
			wsAPI := otRecorderAPI.Group("ws")
			{
				wsAPI.GET("last", func(c *gin.Context) {
					wshandler(c.Writer, c.Request)
				})
			}
		}
	}
	router.GET("/oauth2callback", OauthCallback)
	router.POST("/search/", BleveSearchQuery)
	router.GET("/location/", LocationHandler)
	router.HEAD("/location/", LocationHeadHandler)
}
