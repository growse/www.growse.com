package main

import (
	"github.com/eclipse/paho.mqtt.golang"
	"log"
)

type MQTTMsg struct {
	Type                 string `json: "_type" binding: "required"`
	TrackerId            string `json: "tid" binding: "required"`
	Accuracy             int `json: "acc" binding: "required"`
	Battery              int `json: "batt" binding: "required"`
	Connection           string `json: "conn" binding: "required"`
	Doze                 bool `json: "doze" binding: "required"`
	Latitude             float64 `json: "lat" binding: "required"`
	Longitude            float64 `json: "lon" binding: "required"`
	DeviceTimestampAsInt int `json: "tst" binding:"required"`
}

func SubscribeMQTT(quit <-chan bool) error {

	topic := "owntracks/#"
	log.Print("Connecting to MQTT")
	var mqttClientOptions = mqtt.NewClientOptions()
	mqttClientOptions.AddBroker("tcp://localhost:1883")
	mqttClientOptions.SetClientID("growselocator")
	mqttClientOptions.SetAutoReconnect(true)

	mqttClient := mqtt.NewClient(mqttClientOptions)

	mqttClientToken := mqttClient.Connect()
	defer mqttClient.Disconnect(250)
	if mqttClientToken.Wait() && mqttClientToken.Error() != nil {
		log.Printf("Error connecting to mqtt: %v", mqttClientToken.Error())
		return mqttClientToken.Error()
	}
	log.Print("Connected")

	mqttSubscribeToken := mqttClient.Subscribe(topic, 0, handler)
	if mqttSubscribeToken.Wait() && mqttSubscribeToken.Error() != nil {
		log.Printf("Error connecting to mqtt: %v", mqttSubscribeToken.Error())
		mqttClient.Disconnect(250)
		return mqttSubscribeToken.Error()
	}
	select {
	case <-quit:
		log.Print("Unsubscribing")
		mqttUnsubscribeToken := mqttClient.Unsubscribe(topic)
		if mqttUnsubscribeToken.Wait() && mqttUnsubscribeToken.Error() != nil {
			log.Printf("Error unsubscribing from mqtt: %v", mqttUnsubscribeToken.Error())
		}
		log.Print("Closing MQTT")
		return nil
	}
}

var handler mqtt.MessageHandler = func(client mqtt.Client, msg mqtt.Message) {
	log.Printf("TOPIC: %s\n", msg.Topic())
	log.Printf("MSG: %s\n", msg.Payload())
}