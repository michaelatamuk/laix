plugins {
    kotlin("jvm") version "2.1.20"
    application
}

group = "dev.laix"
version = "0.17.3"

kotlin {
    jvmToolchain(17)
}

application {
    mainClass.set("dev.laix.decision.appkit.cli.MainKt")
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.1")
    testImplementation(kotlin("test-junit5"))
    testImplementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.0")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
}
