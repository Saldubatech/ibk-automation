# Gemini prompts for Cut-Paste

## PlantUml from Case Classes

Create a scala macro that given a Class that may be declared in any reachable compilation unit as its generic parameter generates a plantuml class diagram with:

1. Properties for all fields that extend `AnyVal` or are Option[_] or Seq[_] of types that extend `AnyVal`
2. Directed Composition links to the corresponding class for any fields that are `Seq[_]`, `Map[_, _]` or any other collection of types not derived from AnyVal.
3. All links are labeled with the name of the field.

## Python parallel socket

A Python class that can send messages through a socket and wait for answers from the socket in an asynchronous way.

- The socket will be provided in the constructor.
- Messages have a unique id that is also present in the responses so that they can be correlated with the request.
- The class keeps track of all outstanding requests and pairs them with the responses as they arrive.
- Waiting for responses is asynchronous with requests.
- When a response arrives, the pair of request and response are provided as arguments to a callback function that is also provided in the constructor.
- Add type hints considering that requests and responses are strings.

## Shipment data model

Create a shipment class diagram in PlantUml to represent shipments of goods with the following:

1. A shipment has heading information that identifies


## Journalled Database

Create a SQL database to represent entities in a table with data in Blobs in a versioned way and the corresponding SQL DDL:

1. All versions of an entity have the same `entityId`
2. Each version of an entity have a unique `recordId` and is store in its own record with a complete copy of the Blob payload.
3. Each record also has two timestamps: `recordedAt` and `effectiveAt`
4. `recordedAt` is the time when the record is first written to the Database and must be populated by the database upon insertion.

Create a query to retrieve the record of an entity that has:

1. `entityId` equal to a given parameter.
2. The most recent `recordedAt` that is less than given parameter of `recordBefore`
3. The most recent `effectiveAt` that is less than given parameter of `effectiveBefore`

Using Python and the psycopg2 library, create a method to insert a new record with the following behavior:

1. The method is transactional on any effects on the DB.
2. It takes the entityId, effectiveAt and the data string as arguments.
3. If the `effectiveAt` value is higher than any other record, simply insert the new record with the given parameters.
4. If the `effectiveAt` value is not higher than any other record, then:
   1. insert the record based in the given parameters
   2. Find all records with `effectiveAt` greater than the parameter and that have the largest recordedAt value for a given `effectiveAt` Value.
   3. Insert a copy of this set of records with their given effectiveAt value in a single sql statement with values in order of `effectiveAt`
