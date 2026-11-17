pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
    }
}

dependencyResolutionManagement {
    repositories {
        mavenCentral()
    }
}

rootProject.name = "laix-examples"

// Use the local Kotlin package as a composite build, so the examples always run
// against the working tree instead of a published artifact.
includeBuild("../../packages/kotlin/laix")
