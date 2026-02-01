// Package kling3 provides information about Kling 3 AI platform.
//
// Kling 3 AI is a next-generation AI video creation platform with stunning
// 4K resolution and intelligent motion control.
//
// Official Website: https://kling3.net
package kling3

import "fmt"

// Version is the current version of Kling 3 AI
const Version = "0.1.0"

// Website is the official website URL
const Website = "https://kling3.net"

// PlatformName is the name of the platform
const PlatformName = "Kling 3 AI"

// Description is the platform description
const Description = "Next-generation AI video creation platform"

// Features contains the list of platform features
var Features = []string{
	"Text-to-Video Generation",
	"Image-to-Video Animation",
	"4K Resolution Output (60fps)",
	"Advanced Motion Control",
	"Multi-Format Support",
	"Professional-Grade Quality",
}

// Info represents comprehensive platform information
type Info struct {
	Name        string   `json:"name"`
	Version     string   `json:"version"`
	Website     string   `json:"website"`
	Description string   `json:"description"`
	Features    []string `json:"features"`
}

// GetInfo returns comprehensive platform information
//
// Example:
//
//	info := kling3.GetInfo()
//	fmt.Println(info.Name)
//	fmt.Println(info.Version)
func GetInfo() Info {
	return Info{
		Name:        PlatformName,
		Version:     Version,
		Website:     Website,
		Description: Description,
		Features:    Features,
	}
}

// GetPlatformURL returns the official website URL
//
// Example:
//
//	url := kling3.GetPlatformURL()
//	fmt.Println(url) // Output: https://kling3.net
func GetPlatformURL() string {
	return Website
}

// GetVersion returns the current version
//
// Example:
//
//	version := kling3.GetVersion()
//	fmt.Println(version) // Output: 0.1.0
func GetVersion() string {
	return Version
}

// GetFeatures returns the list of platform features
//
// Example:
//
//	features := kling3.GetFeatures()
//	for _, feature := range features {
//	    fmt.Println("•", feature)
//	}
func GetFeatures() []string {
	return Features
}

// DisplayInfo prints formatted platform information to stdout
//
// Example:
//
//	kling3.DisplayInfo()
func DisplayInfo() {
	fmt.Println()
	fmt.Println("🎬 Kling 3 AI - Next-generation AI Video Creation Platform")
	fmt.Println()
	fmt.Printf("📦 Package: %s\n", PlatformName)
	fmt.Printf("🔖 Version: %s\n", Version)
	fmt.Printf("🌐 Website: %s\n", Website)
	fmt.Printf("📝 Description: %s\n", Description)
	fmt.Println()
	fmt.Println("✨ Features:")
	for _, feature := range Features {
		fmt.Printf("   • %s\n", feature)
	}
	fmt.Println()
	fmt.Printf("🚀 Visit %s to get started!\n", Website)
	fmt.Println()
}
