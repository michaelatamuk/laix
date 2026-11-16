plugins {
    kotlin("jvm") version "2.1.20"
}

group = "dev.laix"
version = "0.17.3"

kotlin {
    jvmToolchain(17)
}

dependencies {
    testImplementation(kotlin("test-junit5"))
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
}
